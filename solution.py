from __future__ import annotations
from typing import *
from bnetbase import Variable, Factor, BN

import csv


def set_permutation(scope: List[Variable]) -> Iterator[list]:
    if len(scope) == 0:
        yield []
    else:
        for value in scope[0].domain():
            scope[0].set_assignment(value)
            for perm in set_permutation(scope[1:]):
                yield [value] + perm


def multiply_factors(Factors: List[Factor]) -> Factor:
    '''Factors is a list of factor objects.
    Return a new factor that is the product of the factors in Factors.
    @return a factor'''
    new_scope = []
    for factor in Factors:
        new_scope += factor.get_scope()
    new_scope = list(set(new_scope))
    new_factor = Factor("multiplied", new_scope)
    for perm in set_permutation(new_scope):
        multiplied_value = 1
        for factor in Factors:
            multiplied_value *= factor.get_value_at_current_assignments()
        new_factor.add_value_at_current_assignment(multiplied_value)
    return new_factor


def restrict_factor(f, var, value):
    '''f is a factor, var is a Variable, and value is a value from var.domain.
    Return a new factor that is the restriction of f by this var = value.
    Don't change f! If f has only one variable its restriction yields a
    constant factor.
    @return a factor'''
    new_scope = [x for x in f.get_scope() if x != var]
    new_factor = Factor("restricted on " + var.name + " = " + str(value) + " " + f.name, new_scope)
    for perm in set_permutation(new_scope):
        var.set_assignment(value)
        new_factor.add_value_at_current_assignment(f.get_value_at_current_assignments())
    return new_factor


def sum_out_variable(f: Factor, var: Variable) -> Factor:
    '''f is a factor, var is a Variable.
    Return a new factor that is the result of summing var out of f, by summing
    the function generated by the product over all values of var.
    @return a factor'''
    new_scope = [x for x in f.get_scope() if x != var]
    new_factor = Factor("summed_out " + f.name, new_scope)
    for perm in set_permutation(new_scope):
        summed = 0
        for value in var.domain():
            var.set_assignment(value)
            summed += f.get_value_at_current_assignments()
        new_factor.add_value_at_current_assignment(summed)
    return new_factor


def normalize(nums: List[float]) -> List[float]:
    '''num is a list of numbers. Return a new list of numbers where the new
    numbers sum to 1, i.e., normalize the input numbers.
    @return a normalized list of numbers'''
    bottom = sum(nums)
    return [x / bottom for x in nums]


def normalize_factor(f: Factor) -> Factor:
    new_scope = f.get_scope()
    new_factor = Factor("normalized", new_scope)
    summed = 0
    for perm in set_permutation(new_scope):
        summed += f.get_value_at_current_assignments()
    for perm in set_permutation(new_scope):
        new_factor.add_value_at_current_assignment(f.get_value_at_current_assignments() / summed)
    return new_factor


def min_fill_ordering(Factors, QueryVar):
    '''Factors is a list of factor objects, QueryVar is a query variable.
    Compute an elimination order given list of factors using the min fill heuristic. 
    Variables in the list will be derived from the scopes of the factors in Factors. 
    Order the list such that the first variable in the list generates the smallest
    factor upon elimination. The QueryVar must NOT part of the returned ordering list.
    @return a list of variables'''
    ### YOUR CODE HERE ###


def VE(Net: BN, QueryVar: Variable, EvidenceVars: List[Variable]) -> List[float]:
    """
    Input: Net---a BN object (a Bayes Net)
           QueryVar---a Variable object (the variable whose distribution
                      we want to compute)
           EvidenceVars---a LIST of Variable objects. Each of these
                          variables has had its evidence set to a particular
                          value from its domain using set_evidence.
     VE returns a distribution over the values of QueryVar, i.e., a list
     of numbers, one for every value in QueryVar's domain. These numbers
     sum to one, and the i'th number is the probability that QueryVar is
     equal to its i'th value given the setting of the evidence
     variables. For example if QueryVar = A with Dom[A] = ['a', 'b',
     'c'], EvidenceVars = [B, C], and we have previously called
     B.set_evidence(1) and C.set_evidence('c'), then VE would return a
     list of three numbers. E.g. [0.5, 0.24, 0.26]. These numbers would
     mean that Pr(A='a'|B=1, C='c') = 0.5 Pr(A='a'|B=1, C='c') = 0.24
     Pr(A='a'|B=1, C='c') = 0.26
     @return a list of probabilities, one for each item in the domain of the QueryVar
     """
    new_factors = [factor for factor in Net.factors()]
    # print("starting factors")
    # for factor in new_factors:
    #     print(factor)
    #     factor.print_table()

    for var in EvidenceVars:
        new_factors = [restrict_factor(factor, var, var.get_evidence()) for factor in new_factors]
    # print("restricted factors")
    # for factor in new_factors:
    #     print(factor)
    #     factor.print_table()
    for variable in Net.variables():
        if variable not in EvidenceVars and variable != QueryVar:
            factors_containing_variable = [factor for factor in new_factors if variable in factor.get_scope()]
            new_factors = [factor for factor in new_factors if factor not in factors_containing_variable]
            new_factors.append(sum_out_variable(multiply_factors(factors_containing_variable), variable))
            # print("summed out factor by var " + variable.name)
            # for factor in new_factors:
            #     factor.print_table()
    # for factor in new_factors:
    #     print(factor)
    #     factor.print_table()
    final_factor = multiply_factors(new_factors)
    # final_factor.print_table()
    result = []
    for perm in set_permutation(final_factor.get_scope()):
        result.append(final_factor.get_value_at_current_assignments())
    return normalize(result)


def normalize_over_salary(factor: Factor):
    if len(factor.get_scope()) == 1:
        return
    scope_without_salary = [x for x in factor.get_scope() if x.name != "Salary"]
    denominator = 0
    salary_factor = [x for x in factor.get_scope() if x.name == "Salary"][0]
    salary_factor.set_assignment(">=50K")
    for perm in set_permutation(scope_without_salary):
        denominator += factor.get_value_at_current_assignments()
    for perm in set_permutation(scope_without_salary):
        factor.add_value_at_current_assignment(factor.get_value_at_current_assignments() / denominator)
    salary_factor.set_assignment("<50K")
    denominator = 0
    for perm in set_permutation(scope_without_salary):
        denominator += factor.get_value_at_current_assignments()
    for perm in set_permutation(scope_without_salary):
        factor.add_value_at_current_assignment(factor.get_value_at_current_assignments() / denominator)

def NaiveBayesModel():
    '''
   NaiveBayesModel returns a BN that is a Naive Bayes model that 
   represents the joint distribution of value assignments to 
   variables in the Adult Dataset from UCI.  Remember a Naive Bayes model
   assumes P(X1, X2,.... XN, Class) can be represented as 
   P(X1|Class)*P(X2|Class)* .... *P(XN|Class)*P(Class).
   When you generated your Bayes Net, assume that the values 
   in the SALARY column of the dataset are the CLASS that we want to predict.
   @return a BN that is a Naive Bayes model and which represents the Adult Dataset. 
    '''
    ### READ IN THE DATA
    input_data = []
    with open('data/adult-train.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader, None)  # skip header row
        for row in reader:
            input_data.append(row)

    ### DOMAIN INFORMATION REFLECTS ORDER OF COLUMNS IN THE DATA SET
    variable_domains = {
        "Work": ['Not Working', 'Government', 'Private', 'Self-emp'],
        "Education": ['<Gr12', 'HS-Graduate', 'Associate', 'Professional', 'Bachelors', 'Masters', 'Doctorate'],
        "MaritalStatus": ['Not-Married', 'Married', 'Separated', 'Widowed'],
        "Occupation": ['Admin', 'Military', 'Manual Labour', 'Office Labour', 'Service', 'Professional'],
        "Relationship": ['Wife', 'Own-child', 'Husband', 'Not-in-family', 'Other-relative', 'Unmarried'],
        "Race": ['White', 'Black', 'Asian-Pac-Islander', 'Amer-Indian-Eskimo', 'Other'],
        "Gender": ['Male', 'Female'],
        "Country": ['North-America', 'South-America', 'Europe', 'Asia', 'Middle-East', 'Carribean'],
        # "Salary": ['<50K', '>=50K']
    }
    salary_variable = Variable("Salary", ['<50K', '>=50K'])
    salary_factor = Factor("Salary", [salary_variable])
    variables = []
    factors = [salary_factor]
    for key, value in variable_domains.items():
        variable = Variable(key, value)
        variables.append(variable)
        factor = Factor(key, [variable, salary_variable])
        factors.append(factor)
    variables.append(salary_variable)

    for row in input_data:
        for i in range(len(variables)):
            variables[i].set_assignment(row[i])
        for factor in factors:
            previous_value = factor.get_value_at_current_assignments()
            factor.add_value_at_current_assignment(previous_value + 1)


    for factor in factors:
        normalize_over_salary(factor)
    return BN("nn", variables, factors)


NaiveBayesModel()


def Explore(Net, question):
    '''    Input: Net---a BN object (a Bayes Net)
           question---an integer indicating the question in HW4 to be calculated. Options are:
           1. What percentage of the women in the data set end up with a P(S=">=$50K"|E1) that is strictly greater than P(S=">=$50K"|E2)?
           2. What percentage of the men in the data set end up with a P(S=">=$50K"|E1) that is strictly greater than P(S=">=$50K"|E2)?
           3. What percentage of the women in the data set with P(S=">=$50K"|E1) > 0.5 actually have a salary over $50K?
           4. What percentage of the men in the data set with P(S=">=$50K"|E1) > 0.5 actually have a salary over $50K?
           5. What percentage of the women in the data set are assigned a P(Salary=">=$50K"|E1) > 0.5, overall?
           6. What percentage of the men in the data set are assigned a P(Salary=">=$50K"|E1) > 0.5, overall?
           @return a percentage (between 0 and 100)
    '''
    # Create a core evidence set (E1) using the values assigned to the following variables: [Work, Occupation, Education, and Relationship Status]
    E1 = [variable for variable in Net.variables() if
          variable.name in ['Work', 'Occupation', 'Education', 'Relationship']]
    # Create an extended evidence set (E2) using the values assigned to the following variables: [Work, Occupation, Education, Relationship Status, and Gender]
    E2 = [variable for variable in Net.variables() if
          variable.name in ['Work', 'Occupation', 'Education', 'Relationship', 'Gender']]
    salary_variable = [variable for variable in Net.variables() if variable.name == 'Salary'][0]
    gender_variable = [variable for variable in Net.variables() if variable.name == 'Gender'][0]
    input_data = []
    with open('data/adult-test.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader, None)  # skip header row
        for row in reader:
            input_data.append(row)
    # Work, Education, MaritalStatus, Occupation, Relationship, Race, Gender, Country, Salary
    names = ["Work", "Education", "Occupation", "Relationship", "Race", "Gender", "Country", "Salary"]
    numerator = 0
    denominator = 0
    for row in input_data:
        for i in range(len(Net.variables())):
            Net.variables()[i].set_evidence(row[i])
        if question == 1:
            if gender_variable.get_evidence() == "Female":
                denominator += 1
                # print(VE(Net, salary_variable, E1)[1], VE(Net, salary_variable, E2)[1])
                if VE(Net, salary_variable, E1)[1] > VE(Net, salary_variable, E2)[1]:
                    numerator += 1
        elif question == 2:
            if gender_variable.get_evidence() == "Male":
                denominator += 1
                if VE(Net, salary_variable, E1)[1] > VE(Net, salary_variable, E2)[1]:
                    numerator += 1
        elif question == 3:
            # print(VE(Net, salary_variable, E1))
            if gender_variable.get_evidence() == "Female" and VE(Net, salary_variable, E1)[1] > 0.5:
                denominator += 1
                if salary_variable.get_evidence() == ">=50K":
                    numerator += 1
        elif question == 4:
            if gender_variable.get_evidence() == "Male" and VE(Net, salary_variable, E1)[1] > 0.5:
                denominator += 1
                if salary_variable.get_evidence() == ">=50K":
                    numerator += 1
        elif question == 5:
            if gender_variable.get_evidence() == "Female":
                denominator += 1
                if VE(Net, salary_variable, E1)[1] > 0.5:
                    numerator += 1
        elif question == 6:
            if gender_variable.get_evidence() == "Male":
                denominator += 1
                if VE(Net, salary_variable, E1)[1] > 0.5:
                    numerator += 1


    # print(numerator, denominator)
    return numerator / denominator * 100


if __name__ == "__main__":
    Net = NaiveBayesModel()
    # for factor in Net.factors():
    #     print(factor.name)
    #     factor.print_table()
    # print(Net.variables()[-1].name)
    # print(VE(Net, Net.variables()[-1], []))
    # print(11360 / (3699 + 11360))
    # print(Explore(Net, 1))
    # print(Explore(Net, 2))
    # print(Explore(Net, 3))
    # print(Explore(Net, 4))
    # print(Explore(Net, 5))
    # print(Explore(Net, 6))

